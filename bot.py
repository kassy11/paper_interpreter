from util import create_prompt, generate


def main():
    arxiv_url = "https://arxiv.org/abs/1706.03762"
    prompt = create_prompt(arxiv_url)
    answer = generate(prompt)
    print(answer)


main()
