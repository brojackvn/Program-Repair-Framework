from src.args import parser
from src.repair import prompt_apr, conversational_apr

def main():
    args = parser.parse_args()

    if args.option == "prompt-apr":
        prompt_apr(args)
    elif args.option == "conversational-apr":
        conversational_apr(args)
    else:
        raise ValueError("Invalid option: {}".format(args.option))

if __name__ == "__main__":
    main()