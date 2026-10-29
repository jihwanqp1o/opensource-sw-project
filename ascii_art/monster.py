"""몬스터 이미지를 명도 기준으로 아스키 문자로 바꾼다."""
from PIL import Image

# 어두운 터미널 기준: 밝은 픽셀일수록 빽빽한 문자
CHARS = " .:-=+*#%@"


def image_to_ascii(path, width=40) -> str:
    img = Image.open(path).convert("RGBA")
    # 터미널 글자는 세로로 길어서 높이를 절반 정도로 줄여야 비율이 맞는다
    height = max(1, int(img.height / img.width * width * 0.5))
    img = img.resize((width, height))

    lines = []
    for y in range(height):
        row = ""
        for x in range(width):
            r, g, b, a = img.getpixel((x, y))
            if a < 128:  # 투명한 부분은 공백
                row += " "
                continue
            brightness = (r * 299 + g * 587 + b * 114) // 1000  # 0~255
            row += CHARS[brightness * (len(CHARS) - 1) // 255]
        lines.append(row.rstrip())
    return "\n".join(lines)


if __name__ == "__main__":
    # 단독 실행: python -m ascii_art.monster
    import config

    print(image_to_ascii(config.MONSTER_IMAGE, config.MONSTER_ART_WIDTH))
