import logging
import sys
import os
from logging.handlers import RotatingFileHandler

def setup_logger(name: str = "SWEAT", log_file: str = "sweat.log") -> logging.Logger:
    """
    Sets up a structured logger that outputs INFO to console and DEBUG to file.
    """
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Avoid adding handlers multiple times if logger is already set up
    if logger.hasHandlers():
        return logger
    
    # Console Handler (Human friendly)
    c_handler = logging.StreamHandler(sys.stdout)
    c_handler.setLevel(logging.INFO)
    c_format = logging.Formatter('➤ %(name)s: %(message)s')
    c_handler.setFormatter(c_format)
    
    # File Handler (Machine friendly / Debug)
    f_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=2)
    f_handler.setLevel(logging.DEBUG)
    f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    f_handler.setFormatter(f_format)
    
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)
    
    return logger

# Global instance
logger = setup_logger()
