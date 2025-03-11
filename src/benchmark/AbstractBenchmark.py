import abc
import os
from os.path import join
from typing import Tuple

class AbstractBenchmark():
    def __init__(self):
        # Initialize the benchmark
        pass
    
    @abc.abstractmethod
    def load_mappings():
        # Load the mapping information
        pass

    @abc.abstractmethod
    def load_info():
        # Load the benchmark information
        pass

    @abc.abstractmethod
    def load_single_info():
        # Load and Checkout a single benchmark information
        pass

    @abc.abstractmethod
    def setup_validation_dir():
        # Setup the environment
        pass

    @abc.abstractmethod
    def clear_validation_dir():
        # Cleanup the environment
        pass

    @abc.abstractmethod
    def execute():
        # Compile and Test the Benchmark
        pass

    @abc.abstractmethod
    def validate():
        # Validate all the generated patches
        pass