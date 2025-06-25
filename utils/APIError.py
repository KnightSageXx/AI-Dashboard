class APIError(Exception):
    """Custom exception for API errors
    
    This exception is used to represent errors that occur during API operations.
    It includes a message and a status code that can be used to generate an
    appropriate HTTP response.
    """
    
    def __init__(self, message, status_code=500):
        """Initialize the APIError
        
        Args:
            message (str): The error message
            status_code (int): The HTTP status code
        """
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)