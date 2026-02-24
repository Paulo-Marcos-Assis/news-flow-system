class ErrorQueueException(Exception):
    """
    Exception raised for general errors that don't require routing to the fail queue.
    """

    def __init__(self, message="A general error occurred during message processing."):
        super().__init__(message)