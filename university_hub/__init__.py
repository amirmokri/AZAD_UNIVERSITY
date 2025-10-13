# This will ensure that PyMySQL is used as the MySQL driver
# Required for some environments where mysqlclient is not available
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass
