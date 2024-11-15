class MultiDBRouter:
    """
    A router to control all database operations on models.
    """

    def db_for_read(self, model, **hints):
        if model._meta.model_name == 'meta':
            return 'rawdb'
        elif model._meta.app_label == 'auth' or model._meta.model_name in ['user', 'profile']:
            return 'default'
        return 'default'

    def db_for_write(self, model, **hints):
        if model._meta.model_name == 'meta':
            return 'rawdb'
        elif model._meta.app_label == 'auth' or model._meta.model_name in ['user', 'profile']:
            return 'default'
        return 'default'


    def allow_relation(self, obj1, obj2, **hints):
        """Allow relations only if models are in the same database."""
        if obj1._state.db == obj2._state.db:
            return True  # Allow relations if both objects are in the same database
        return None  # Disallow relations otherwise

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if db == 'default':
            return app_label in ('auth', 'contenttypes', 'sessions', 'admin', 'myapp', 'common')
        elif db == 'rawdb':
            return model_name == 'meta'
        return None