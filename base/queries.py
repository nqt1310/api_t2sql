class DBQuery:
    @staticmethod
    def get_full_meta():
        return """
        select * from public.metadata
        """
    