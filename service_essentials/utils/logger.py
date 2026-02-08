import os
import datetime

class Logger:
    """
    A Logger class to log messages either to the console or a log file.

    Attributes:
        log_to_console (bool): If True, logs will be displayed on the console.
        log_to_file (bool): If True, logs will be saved to a file.
        log_file_path (str): Path of the log file where messages are stored.
        service (Service): The service instance containing the config information.
    """
    
    def __init__(self, service=None, log_to_console=False, log_to_file=True, log_file_base=''):
        """
        Initializes the Logger instance with an Experiment.

        Args:
            experiment (Experiment): The Experiment instance containing the configuration.
            log_to_console (bool): If True, logs are shown on the console.
            log_to_file (bool): If True, logs are written to a log file.
            log_file_base (str): Base name of the log file (timestamp will be added).
        """
        self.service = service
        self.log_to_console = log_to_console
        self.log_to_file = log_to_file
        self.base_path = os.path.join("logs")
        self.verbose = os.getenv("VERBOSE", "none")

        if log_file_base == '': log_file_base = "log"

        self.log_file_path = os.path.join(self.base_path,self._create_timestamped_filename(log_file_base))

        #make sure that the logs directory exists
        os.makedirs(self.base_path, exist_ok=True)

        # Initialize the log file with the service configuration information
        if self.log_to_file:
            with open(self.log_file_path, 'w') as file:
                file.write(self._get_service_info_header())


    def _get_timestamp(self):
        """
        Generates a timestamp for the log entry.

        Returns:
            str: Current date and time in a formatted string.
        """
        return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def _create_timestamped_filename(self, base_name):
        """
        Creates a unique filename by appending a timestamp to the base name.

        Args:
            base_name (str): The base name for the log file.

        Returns:
            str: A unique log file name with the current timestamp.
        """
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{base_name}_{timestamp}.txt"

    def _get_service_info_header(self):
        """
        Generates the log file header with service configuration details.

        Returns:
            str: A formatted string with the service's configuration details.
        """
        header = f"--- Logging started at {self._get_timestamp()} ---\n"
        if self.service:
            header += f"""
            Service: {self.service.service_name}"
            InputQueue:{self.service.input_queue},OutputQueue:{self.service.output_queue},FailQueue:{self.service.fail_queue},ErrorQueue:{self.service.error_queue} \n"""
        else:
            header = "No service associated to the logger\n"

        return header

    def _log(self, level, message):
        """
        Internal method to format and handle the logging message.

        Args:
            level (str): The severity level of the log (e.g., INFO, WARNING, ERROR).
            message (str): The log message to be recorded.
        """
        timestamp = self._get_timestamp()
        log_message = f"[{timestamp}] [{level}] {message}"

        # Print to console
        if self.log_to_console:
            print(log_message)

        # Write to file
        if self.log_to_file:
            with open(self.log_file_path, 'a') as file:
                file.write(log_message + '\n')

    def info(self, message):
        """
        Logs an INFO level message.

        Args:
            message (str): The informational message to log.
        """
        if self.verbose == "all":
            self._log("INFO", message)

    def warning(self, message):
        """
        Logs a WARNING level message.

        Args:
            message (str): The warning message to log.
        """
        if self.verbose == "all" or self.verbose == "we":
            self._log("WARNING", message)

    def error(self, message):
        """
        Logs an ERROR level message.

        Args:
            message (str): The error message to log.
        """
        if self.verbose == "all" or self.verbose == "we":
            self._log("ERROR", message)

    def debug(self, message):
        """
        Logs a DEBUG level message.

        Args:
            message (str): The debug message to log.
        """
        if self.verbose == "all" or self.verbose == "de":
            self._log("DEBUG", message)
