import re
from typing import Dict, Any
from datetime import time as dtime

import pandas as pd
from django.db import transaction

from classes.models import Course, Teacher, Floor, Room, ClassSchedule, ImportJob, Faculty


DAY_MAP = {
    'شنبه': 'saturday',
    'یکشنبه': 'sunday',
    'دوشنبه': 'monday',
    'سه‌شنبه': 'tuesday',
    'سه شنبه': 'tuesday',
    'چهارشنبه': 'wednesday',
    'پنجشنبه': 'thursday',
    'جمعه': 'friday',
}

CAL_REGEX = re.compile(r"(\S+)\s+(\d{1,2}:\d{2})\s*تا\s*(\d{1,2}:\d{2})")


def _safe_time(val: str):
    h, m = val.split(':')
    return dtime(hour=int(h), minute=int(m))


def _normalize_text(value: str) -> str:
    """Normalize Persian headers: trim, unify ye/ke, collapse spaces."""
    if value is None:
        return ''
    text = str(value).strip()
    # Arabic ye/kaf to Persian
    text = text.replace('\u064a', '\u06cc').replace('\u0643', '\u06a9')
    # Remove zero-width and non-breaking spaces
    text = text.replace('\u200c', ' ').replace('\xa0', ' ')
    # Collapse multiple spaces
    text = re.sub(r"\s+", " ", text)
    return text


def _get_error_suggestions(error_type: str, error_message: str, row_data) -> list:
    """
    Generate helpful suggestions for fixing import errors.
    
    Args:
        error_type: Categorized error type
        error_message: Original error message
        row_data: Raw row data for context
        
    Returns:
        List of suggestion strings
    """
    suggestions = []
    
    if error_type == 'parsing_errors':
        suggestions.extend([
            "بررسی کنید که فرمت تقویم به صورت 'روز ساعت شروع تا ساعت پایان' باشد",
            "مثال صحیح: 'شنبه 08:00 تا 10:00'",
            "اطمینان حاصل کنید که نام روز به فارسی نوشته شده باشد"
        ])
    elif error_type == 'missing_course_code':
        suggestions.extend([
            "کد درس نمی‌تواند خالی باشد",
            "لطفاً کد درس را در ستون 'کد درس' وارد کنید"
        ])
    elif error_type == 'invalid_day':
        suggestions.extend([
            "روزهای معتبر: شنبه، یکشنبه، دوشنبه، سه‌شنبه، چهارشنبه، پنجشنبه، جمعه",
            "بررسی کنید که نام روز به درستی نوشته شده باشد"
        ])
    elif error_type == 'room_conflict_errors':
        suggestions.extend([
            "این اتاق در این زمان قبلاً رزرو شده است",
            "لطفاً اتاق، روز یا زمان دیگری انتخاب کنید",
            "بررسی کنید که آیا کلاس دیگری در همین زمان در این اتاق وجود دارد"
        ])
    elif error_type == 'teacher_conflict_errors':
        suggestions.extend([
            "این استاد در این زمان کلاس دیگری دارد",
            "لطفاً استاد، روز یا زمان دیگری انتخاب کنید",
            "بررسی کنید که آیا استاد در همین زمان کلاس دیگری تدریس می‌کند"
        ])
    elif error_type == 'time_conflict_errors':
        suggestions.extend([
            "تداخل زمانی در برنامه‌ریزی کلاس‌ها",
            "لطفاً زمان‌های کلاس‌ها را بررسی کنید",
            "اطمینان حاصل کنید که کلاس‌ها همزمان نباشند"
        ])
    elif error_type == 'duplicate_schedules':
        suggestions.extend([
            "این برنامه کلاسی قبلاً وجود دارد",
            "بررسی کنید که آیا این کلاس قبلاً وارد شده است",
            "در صورت نیاز، از گزینه 'بروزرسانی' استفاده کنید"
        ])
    elif error_type == 'data_quality_issues':
        suggestions.extend([
            "کیفیت داده‌ها را بررسی کنید",
            "اطمینان حاصل کنید که تمام فیلدهای ضروری پر شده باشند",
            "بررسی کنید که فرمت داده‌ها صحیح باشد"
        ])
    elif error_type == 'invalid_duration':
        suggestions.extend([
            "مدت زمان کلاس باید بین 30 دقیقه تا 6 ساعت باشد",
            "بررسی کنید که ساعت شروع و پایان صحیح باشد",
            "مثال صحیح: 08:00 تا 10:30"
        ])
    elif error_type == 'missing_time_data':
        suggestions.extend([
            "ساعت شروع و پایان کلاس باید مشخص باشد",
            "بررسی کنید که ستون تقویم کلاس درس پر شده باشد",
            "فرمت صحیح: 'روز ساعت شروع تا ساعت پایان'"
        ])
    else:
        suggestions.append("لطفاً خطا را بررسی کرده و دوباره تلاش کنید")
    
    return suggestions


# Canonical field names we expect -> possible header aliases in Excel (Persian/English variants)
COLUMN_ALIASES = {
    'کد درس': ['کد درس', 'كد درس', 'کدِ درس', 'Course Code', 'کد-درس'],
    'نام درس': ['نام درس', 'نامِ درس', 'Course Name', 'عنوان درس'],
    'تقويم كلاس درس': ['تقويم كلاس درس', 'تقویم کلاس درس', 'تقويم کلاس درس', 'تقویمِ کلاس', 'تقويم', 'Calendar'],
    'نام كامل استاد': ['نام كامل استاد', 'نام کامل استاد', 'استاد', 'نام استاد', 'Teacher Name'],
    'نام مكان': ['نام مكان', 'نام مکان', 'کلاس', 'اتاق', 'Room', 'Room Name', 'محل برگزاری'],
    'تعداد واحد نظري': ['تعداد واحد نظري', 'تعداد واحد نظری', 'نظری', 'Theory Units'],
}


def _map_headers(df: pd.DataFrame) -> pd.DataFrame:
    """Rename DataFrame columns to canonical Persian names using aliases and normalization."""
    normalized_cols = {_normalize_text(c): c for c in df.columns}
    rename_map = {}
    found = set()
    for canonical, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            norm_alias = _normalize_text(alias)
            if norm_alias in normalized_cols:
                original = normalized_cols[norm_alias]
                rename_map[original] = canonical
                found.add(canonical)
                break
    if rename_map:
        df = df.rename(columns=rename_map)
    return df


def import_ai_excel(path: str, faculty: Faculty, semester: str, academic_year: str, dry_run: bool = True) -> Dict[str, Any]:
    """
    Import AI faculty Excel into ClassSchedule with idempotent upsert.
    
    This function provides comprehensive Excel import functionality with:
    - Detailed error logging and categorization
    - Data validation and quality checks
    - Time conflict validation is SKIPPED during import to allow overlapping schedules
    - Progress tracking and reporting
    
    IMPORTANT: Time validation is disabled during import to prevent errors from
    overlapping schedules. This allows you to import all data first and then
    resolve conflicts manually afterward.
    
    Args:
        path: Path to the Excel file to import
        faculty: Faculty instance to import schedules for
        semester: Semester name (e.g., "نیمسال اول")
        academic_year: Academic year (e.g., "1403-1404")
        dry_run: If True, perform validation without saving data
        
    Returns:
        dict: Import results with counts, errors, and detailed statistics
    """
    # Try read first sheet if Sheet1 missing
    try:
        df = pd.read_excel(path, sheet_name='Sheet1')
    except Exception:
        df = pd.read_excel(path)

    # Normalize and alias-map headers
    df.columns = [_normalize_text(c) for c in df.columns]
    df = _map_headers(df)

    # Required columns based on user's Excel
    required_cols = ['کد درس', 'نام درس', 'تقويم كلاس درس', 'نام كامل استاد', 'نام مكان', 'تعداد واحد نظري']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(
            "ستون‌های مورد نیاز یافت نشد: " + ", ".join(missing) +
            "\nستون‌های موجود: " + ", ".join(map(str, df.columns))
        )

    total = 0
    inserted = 0
    updated = 0
    errors = []
    
    # Enhanced logging for debugging
    import logging
    logger = logging.getLogger(__name__)
    
    # Track detailed import statistics
    import_stats = {
        'courses_created': 0,
        'courses_updated': 0,
        'teachers_created': 0,
        'teachers_updated': 0,
        'rooms_created': 0,
        'rooms_updated': 0,
        'floors_created': 0,
        'schedules_created': 0,
        'schedules_updated': 0,
        'validation_errors': 0,
        'parsing_errors': 0,
        'missing_course_code': 0,
        'invalid_day': 0,
        'time_conflict_errors': 0,
        'room_conflict_errors': 0,
        'teacher_conflict_errors': 0,
        'duplicate_schedules': 0,
        'data_quality_issues': 0,
        'validation_skipped': 0,
    }

    job_kwargs = dict(
        faculty=faculty,
        semester=semester,
        academic_year=academic_year,
        source_filename=str(path),
        total=0,
        inserted=0,
        updated=0,
        errors_json=[],
        dry_run=dry_run,
        status='pending',
    )
    job = ImportJob.objects.create(**job_kwargs)

    try:
        with transaction.atomic():
            # We'll create floors dynamically based on room numbers

            for idx, row in df.iterrows():
                total += 1
                try:
                    course_code = _normalize_text(row.get('کد درس'))
                    course_name = _normalize_text(row.get('نام درس'))
                    teacher_code = ''  # not provided in this Excel
                    teacher_name = _normalize_text(row.get('نام كامل استاد'))
                    room_name = _normalize_text(row.get('نام مكان')) or 'نامشخص'
                    cal_text = _normalize_text(row.get('تقويم كلاس درس'))
                    # Strip trailing Persian/ASCII semicolons and extra chars
                    cal_text = cal_text.rstrip('؛; ')

                    def _to_int(v):
                        try:
                            return int(float(v))
                        except Exception:
                            return 0
                    theory = _to_int(row.get('تعداد واحد نظري'))
                    # If theory blank/zero, default to 1 per user's rule
                    credit_hours = theory if theory > 0 else 1

                    m = CAL_REGEX.search(cal_text)
                    if not m:
                        raise ValueError(f"قالب تقویم نامعتبر: {cal_text}")
                    day_fa, start_s, end_s = m.group(1), m.group(2), m.group(3)
                    day_en = DAY_MAP.get(day_fa)
                    if not day_en:
                        raise ValueError(f"روز نامعتبر: {day_fa}")

                    start_time = _safe_time(start_s)
                    end_time = _safe_time(end_s)

                    # Upsert Course
                    if not course_code:
                        raise ValueError("کد درس خالی است")
                    course, course_created = Course.objects.update_or_create(
                        course_code=course_code,
                        defaults={
                            'course_name': course_name or course_code,
                            'credit_hours': credit_hours,
                            'faculty': faculty,
                            'is_active': True,
                        }
                    )
                    if course_created:
                        import_stats['courses_created'] += 1
                        logger.info(f"Created course: {course_code} - {course_name}")
                    else:
                        import_stats['courses_updated'] += 1
                        logger.info(f"Updated course: {course_code} - {course_name}")

                    # Validate teacher data
                    if not teacher_name and teacher_code:
                        teacher_name = teacher_code
                    if not teacher_name or len(teacher_name.strip()) == 0:
                        teacher_name = 'نامشخص'
                        logger.warning(f"Row {int(idx) + 2}: Teacher name is empty, using default 'نامشخص'")
                    # Prefer matching by (faculty, phone_number) when code exists, else by (faculty, full_name)
                    teacher_created = False
                    if teacher_code:
                        teacher, teacher_created = Teacher.objects.get_or_create(
                            faculty=faculty,
                            phone_number=teacher_code,
                            defaults={'full_name': teacher_name or teacher_code, 'is_active': True}
                        )
                        # Ensure name is up to date
                        if teacher_name and teacher.full_name != teacher_name:
                            teacher.full_name = teacher_name
                            teacher.save(update_fields=['full_name'])
                    else:
                        teacher, teacher_created = Teacher.objects.get_or_create(
                            faculty=faculty,
                            full_name=teacher_name,
                            defaults={'is_active': True}
                        )
                    if teacher_code and teacher.phone_number != teacher_code:
                        teacher.phone_number = teacher_code
                        teacher.save(update_fields=['phone_number'])
                    
                    if teacher_created:
                        import_stats['teachers_created'] += 1
                        logger.info(f"Created teacher: {teacher_name}")
                    else:
                        import_stats['teachers_updated'] += 1

                    # Extract floor number from room number using tens digit
                    # 318 → floor 1 (tens: 1), 324 → floor 2 (tens: 2), 389 → floor 8 (tens: 8)
                    floor_number = 0
                    if room_name and room_name.isdigit():
                        room_num = int(room_name)
                        if room_num >= 10:
                            # Get tens digit for floor number
                            floor_number = (room_num // 10) % 10
                        else:
                            floor_number = 0  # Single digit rooms go to floor 0
                    elif room_name:
                        # Try to extract number from room name
                        import re
                        numbers = re.findall(r'\d+', room_name)
                        if numbers:
                            room_num = int(numbers[0])
                            if room_num >= 10:
                                floor_number = (room_num // 10) % 10
                            else:
                                floor_number = 0
                    
                    # Create floor based on room number
                    floor, floor_created = Floor.objects.get_or_create(
                        faculty=faculty,
                        floor_number=floor_number,
                        defaults={
                            'floor_name': f'طبقه {floor_number}' if floor_number > 0 else 'نامشخص',
                            'is_active': True
                        }
                    )
                    if floor_created:
                        import_stats['floors_created'] += 1
                        logger.info(f"Created floor: {floor_number} for room {room_name}")

                    # Validate room data
                    if not room_name or len(room_name.strip()) == 0:
                        raise ValueError("نام اتاق نمی‌تواند خالی باشد")
                    
                    # Upsert Room on the correct floor
                    room, room_created = Room.objects.get_or_create(
                        floor=floor,
                        room_number=room_name,
                        defaults={
                            'capacity': 0,
                            'room_type': 'classroom',
                            'position': 'left',
                            'is_active': True,
                        }
                    )
                    if room_created:
                        import_stats['rooms_created'] += 1
                        logger.info(f"Created room: {room_name} on floor {floor_number}")
                    else:
                        import_stats['rooms_updated'] += 1

                    # Validate schedule data before creating/updating
                    if not start_time or not end_time:
                        raise ValueError("ساعت شروع و پایان کلاس باید مشخص باشد")
                    
                    if start_time >= end_time:
                        raise ValueError("ساعت پایان باید بعد از ساعت شروع باشد")
                    
                    # Check for reasonable duration (30 minutes to 6 hours)
                    try:
                        # Calculate duration in hours, handling day overflow
                        start_minutes = start_time.hour * 60 + start_time.minute
                        end_minutes = end_time.hour * 60 + end_time.minute
                        
                        # Handle case where end time is next day
                        if end_minutes <= start_minutes:
                            end_minutes += 24 * 60  # Add 24 hours in minutes
                        
                        duration_hours = (end_minutes - start_minutes) / 60.0
                        
                        if duration_hours < 0.5:
                            raise ValueError("مدت زمان کلاس باید حداقل 30 دقیقه باشد")
                        elif duration_hours > 6:
                            raise ValueError("مدت زمان کلاس نمی‌تواند بیش از 6 ساعت باشد")
                    except (AttributeError, TypeError) as e:
                        raise ValueError(f"خطا در محاسبه مدت زمان کلاس: {str(e)}")
                    
                    # Upsert Schedule keyed by (room, day_of_week, start_time, end_time, semester)
                    # Skip validation during import to allow time conflicts
                    
                    # First try to get existing schedule
                    schedule = ClassSchedule.objects.filter(
                        room=room,
                        day_of_week=day_en,
                        start_time=start_time,
                        end_time=end_time,
                        semester=semester
                    ).first()
                    
                    if schedule:
                        # Update existing schedule
                        schedule.course = course
                        schedule.teacher = teacher
                        schedule.academic_year = academic_year
                        schedule.is_active = True
                        schedule._skip_validation = True  # Set flag to skip validation
                        schedule.save()
                        created = False
                    else:
                        # Create new schedule without validation
                        schedule = ClassSchedule(
                            room=room,
                            day_of_week=day_en,
                            start_time=start_time,
                            end_time=end_time,
                            semester=semester,
                            course=course,
                            teacher=teacher,
                            academic_year=academic_year,
                            is_active=True,
                        )
                        schedule._skip_validation = True  # Set flag to skip validation
                        schedule.save()
                        created = True
                        
                    import_stats['validation_skipped'] += 1

                    if created:
                        inserted += 1
                        import_stats['schedules_created'] += 1
                        logger.info(f"Created schedule (validation skipped): {course_name} - {teacher_name} - {day_en} {start_time}-{end_time}")
                    else:
                        updated += 1
                        import_stats['schedules_updated'] += 1
                        logger.info(f"Updated schedule (validation skipped): {course_name} - {teacher_name} - {day_en} {start_time}-{end_time}")

                except Exception as e:  # collect row error, continue
                    # Enhanced error logging with detailed context
                    logger.error(f"Row {int(idx) + 2} failed: {str(e)}")
                    
                    # Categorize error type with more specific detection
                    error_type = 'unknown'
                    error_message = str(e)
                    
                    if 'قالب تقویم نامعتبر' in error_message:
                        error_type = 'parsing_errors'
                        import_stats['parsing_errors'] += 1
                    elif 'ValidationError' in str(e.__class__.__name__):
                        error_type = 'validation_errors'
                        import_stats['validation_errors'] += 1
                        # Check for specific validation errors
                        if 'تداخل زمانی' in error_message and 'اتاق' in error_message:
                            error_type = 'room_conflict_errors'
                            import_stats['room_conflict_errors'] += 1
                        elif 'تداخل زمانی' in error_message and 'استاد' in error_message:
                            error_type = 'teacher_conflict_errors'
                            import_stats['teacher_conflict_errors'] += 1
                        elif 'تداخل زمانی' in error_message:
                            error_type = 'time_conflict_errors'
                            import_stats['time_conflict_errors'] += 1
                    elif 'کد درس خالی' in error_message:
                        error_type = 'missing_course_code'
                        import_stats['missing_course_code'] += 1
                    elif 'روز نامعتبر' in error_message:
                        error_type = 'invalid_day'
                        import_stats['invalid_day'] += 1
                    elif 'duplicate' in error_message.lower() or 'already exists' in error_message.lower():
                        error_type = 'duplicate_schedules'
                        import_stats['duplicate_schedules'] += 1
                    elif 'data quality' in error_message.lower() or 'invalid data' in error_message.lower():
                        error_type = 'data_quality_issues'
                        import_stats['data_quality_issues'] += 1
                    elif 'مدت زمان کلاس' in error_message:
                        error_type = 'invalid_duration'
                        import_stats['data_quality_issues'] += 1
                    elif 'ساعت شروع و پایان' in error_message:
                        error_type = 'missing_time_data'
                        import_stats['data_quality_issues'] += 1
                    
                    # Ensure JSON-serializable values (normalize to string)
                    def _s(v):
                        try:
                            return _normalize_text(v)
                        except Exception:
                            return str(v)
                    
                    error_detail = {
                        'row': int(idx) + 2,  # +2 for header + 1-indexing
                        'error_type': error_type,
                        'error_message': error_message,
                        'error_class': str(e.__class__.__name__),
                        'raw_data': {
                            'course_code': _s(row.get('کد درس')),
                            'course_name': _s(row.get('نام درس')),
                            'calendar': _s(row.get('تقويم كلاس درس')),
                            'teacher_name': _s(row.get('نام كامل استاد')),
                            'room_name': _s(row.get('نام مكان')),
                            'theory_units': _s(row.get('تعداد واحد نظري')),
                        },
                        'suggestions': _get_error_suggestions(error_type, error_message, row)
                    }
                    
                    errors.append(error_detail)

            # If dry run, rollback
            if dry_run:
                transaction.set_rollback(True)

        job.status = 'completed'
    except Exception as e:
        job.status = 'failed'
        errors.append({'row': None, 'error': str(e)})
    finally:
        job.total = total
        job.inserted = inserted
        job.updated = updated
        job.errors_json = errors
        job.save(update_fields=['status', 'total', 'inserted', 'updated', 'errors_json'])

    # Log comprehensive summary
    logger.info("=" * 80)
    logger.info("📊 IMPORT SUMMARY REPORT")
    logger.info("=" * 80)
    logger.info(f"📈 Total rows processed: {total}")
    logger.info(f"✅ Schedules created: {inserted}")
    logger.info(f"🔄 Schedules updated: {updated}")
    logger.info(f"❌ Total errors: {len(errors)}")
    logger.info(f"📊 Success rate: {((inserted + updated) / total * 100):.1f}%" if total > 0 else "N/A")
    logger.info("")
    logger.info("⚠️  NOTE: Time validation was skipped during import to allow time conflicts.")
    logger.info("   Please review and resolve any scheduling conflicts manually after import.")
    logger.info("")
    logger.info("📋 DETAILED STATISTICS:")
    logger.info(f"  📚 Courses - Created: {import_stats['courses_created']}, Updated: {import_stats['courses_updated']}")
    logger.info(f"  👨‍🏫 Teachers - Created: {import_stats['teachers_created']}, Updated: {import_stats['teachers_updated']}")
    logger.info(f"  🚪 Rooms - Created: {import_stats['rooms_created']}, Updated: {import_stats['rooms_updated']}")
    logger.info(f"  🏢 Floors - Created: {import_stats['floors_created']}")
    logger.info(f"  📅 Schedules - Created: {import_stats['schedules_created']}, Updated: {import_stats['schedules_updated']}")
    logger.info("")
    logger.info("❌ ERROR BREAKDOWN:")
    logger.info(f"  🔍 Parsing errors: {import_stats['parsing_errors']}")
    logger.info(f"  ⚠️  Validation errors: {import_stats['validation_errors']}")
    logger.info(f"  📝 Missing course codes: {import_stats['missing_course_code']}")
    logger.info(f"  📅 Invalid days: {import_stats['invalid_day']}")
    logger.info(f"  🚪 Room conflicts: {import_stats['room_conflict_errors']}")
    logger.info(f"  👨‍🏫 Teacher conflicts: {import_stats['teacher_conflict_errors']}")
    logger.info(f"  ⏰ Time conflicts: {import_stats['time_conflict_errors']}")
    logger.info(f"  🔄 Duplicate schedules: {import_stats['duplicate_schedules']}")
    logger.info(f"  📊 Data quality issues: {import_stats['data_quality_issues']}")
    logger.info(f"  ⚠️  Validation skipped: {import_stats['validation_skipped']}")
    
    if errors:
        logger.info("")
        logger.info("🔍 DETAILED ERROR ANALYSIS:")
        error_types = {}
        for error in errors:
            error_type = error.get('error_type', 'unknown')
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        for error_type, count in error_types.items():
            logger.info(f"  {error_type}: {count}")
            
        # Show sample errors for each type
        logger.info("")
        logger.info("📝 SAMPLE ERRORS BY TYPE:")
        shown_types = set()
        for error in errors[:10]:  # Show first 10 errors as samples
            error_type = error.get('error_type', 'unknown')
            if error_type not in shown_types:
                shown_types.add(error_type)
                logger.info(f"  {error_type.upper()}:")
                logger.info(f"    Row {error.get('row', 'N/A')}: {error.get('error_message', 'No message')}")
                if error.get('suggestions'):
                    logger.info(f"    💡 Suggestions: {error['suggestions'][0]}")
                logger.info("")
    
    logger.info("=" * 80)
    logger.info("✅ IMPORT COMPLETED")
    logger.info("=" * 80)

    return {
        'total': total,
        'inserted': inserted,
        'updated': updated,
        'errors': errors,
        'dry_run': dry_run,
        'job_id': job.id,
        'detailed_stats': import_stats,
    }


