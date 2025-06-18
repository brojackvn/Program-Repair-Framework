from src.args import parser
from src.repair import create_repair_instance

def main():
    args = parser.parse_args()
    # Create the repair instance based on the parsed arguments
    repair_instance = create_repair_instance(args)
    # Execute the repair process
    repair_instance.repair()

if __name__ == "__main__":
    main()