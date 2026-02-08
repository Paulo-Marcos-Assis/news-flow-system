class FailQueueException(Exception):
    """
    Exception raised when a message should be routed to the fail queue.
    """

    def __init__(self, message="Message failed and requires routing to the fail queue."):
        super().__init__(message)