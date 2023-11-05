def add_mention(user_id, text):
    return f"<@{user_id}>\n{text}"


def build_image_blocks(figure_paths):
    blocks = []
    for figure_path in figure_paths:
        blocks.append(
            {
                "type": "image",
                "title": {
                    "type": "plain_text",
                    "text": "Please enjoy this photo of a kitten",
                },
                "image_url": figure_path,
                # TODO: テキストを追加
                "alt_text": "An incredibly cute kitten.",
            },
        )
    return blocks
