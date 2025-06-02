from src.args import parser
from src.repair import prompt_apr, conversational_apr, prompt_apr_with_bic, conversational_apr_with_bic

def main():
    args = parser.parse_args()

    if args.option == "prompt-apr":
        prompt_apr(args)
    elif args.option == "conversational-apr":
        conversational_apr(args)
    elif args.option == "prompt-apr-with-bic":
        prompt_apr_with_bic(args)
    elif args.option == "conversational-apr-with-bic":
        conversational_apr_with_bic(args)
    else:
        raise ValueError("Invalid option: {}".format(args.option))

if __name__ == "__main__":
    main()