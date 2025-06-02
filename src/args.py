import argparse

from argparse import HelpFormatter
from operator import attrgetter

class SortingHelpFormatter(HelpFormatter):
    def add_arguments(self, actions):
        actions = sorted(actions, key=attrgetter("option_strings"))
        super(SortingHelpFormatter, self).add_arguments(actions)

def common_args(parser):
    # Common arguments / Environment arguments
    parser.add_argument("--dataset", type=str, required=True, help="Name of the dataset.")
    parser.add_argument("--data-id", type=str, required=True, help="ID of the program to be repaired.")
    parser.add_argument("--input-dir", type=str, required=True, help="Path to the program repair dataset.")
    parser.add_argument("--mapping-dir", type=str, required=True, help="Path to the dataset metadata.")
    parser.add_argument("--output-dir", type=str, required=True, help="Path to the output directory.")
    parser.add_argument("--tmp-dir", type=str, default="tmp/apr-experiments", help="Path to the temporary directory.")
    parser.add_argument("--env-dir", type=str, required=True, help="Path to the environment directory.")
    parser.add_argument('--early-stop', action='store_true', default=False, help="Stop when a plausible patch is found (default: False).")
    parser.add_argument("--time-limit", default=1800, type=int, help="Timeout in seconds (default: 1800).")

def prompt_repair_args(parser):
    # Environment arguments
    common_args(parser)
    # Prompt repair arguments
    parser.add_argument("--sample-size", type=int, default=50, help="Number of samples to generate (default: 5).")
    # Model arguments
    parser.add_argument("--model-name", type=str, required=True, help="Name or path to the repair tool.")
    parser.add_argument("--temperature", type=float, default=0.7, help="Temperature for sampling (default: 0.7).")
    parser.add_argument("--top-p", type=float, default=0.95, help="Top-p for sampling (default: 0.95).")
    parser.add_argument("--top-k", type=int, default=None, help="Top-k for sampling (default: 50).")
    parser.add_argument("--frequency-penalty", type=float, default=None, help="Frequency penalty for sampling (default: 0.0).")
    parser.add_argument("--presence-penalty", type=float, default=None, help="Presence penalty for sampling (default: -0.5).")

def conversational_repair_args(parser):
    # Environment arguments
    common_args(parser)
    # Conversational repair arguments
    parser.add_argument("--attempts", type=int, default=25, help="Number of attempts to generate a patch (default: 5).")
    parser.add_argument("--iterations", type=int, default=5, help="Number of iterations for the conversational repair (default: 5).")
    # Model arguments
    parser.add_argument("--model-name", type=str, required=True, help="Name or path to the repair tool.")
    parser.add_argument("--temperature", type=float, default=0.7, help="Temperature for sampling (default: 0.7).")
    parser.add_argument("--top-p", type=float, default=0.95, help="Top-p for sampling (default: 0.95).")
    parser.add_argument("--top-k", type=int, default=None, help="Top-k for sampling (default: 50).")
    parser.add_argument("--frequency-penalty", type=float, default=None, help="Frequency penalty for sampling (default: 0.0).")
    parser.add_argument("--presence-penalty", type=float, default=None, help="Presence penalty for sampling (default: -0.5).")

parser = argparse.ArgumentParser(
    usage="API-REPAIR FRAMEWORK",
    formatter_class=SortingHelpFormatter,
    add_help=False
)

subparsers = parser.add_subparsers(dest="option", required=True)

# Prompt repair subparser
prompt_repair_parser = subparsers.add_parser("prompt-apr", help="Prompt-based repair")
prompt_repair_args(prompt_repair_parser)

# Conversational repair subparser
conversational_repair_parser = subparsers.add_parser("conversational-apr", help="Conversational repair")
conversational_repair_args(conversational_repair_parser)

# Prompt repair with BIC subparser
prompt_repair_with_bic_parser = subparsers.add_parser("prompt-apr-with-bic", help="Prompt-based repair with BIC")
prompt_repair_args(prompt_repair_with_bic_parser)

# Conversational repair with BIC subparser
conversational_repair_with_bic_parser = subparsers.add_parser("conversational-apr-with-bic", help="Conversational repair with BIC")
conversational_repair_args(conversational_repair_with_bic_parser)