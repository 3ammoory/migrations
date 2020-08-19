class ExistingMigrationError(Exception):
    pass


class EmptyContentError(Exception):
    pass


class UnidentifiedSQLError(Exception):
    pass


class NoMigrationsError(Exception):
    pass
