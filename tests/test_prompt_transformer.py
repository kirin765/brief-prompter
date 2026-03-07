from app.adapters.prompt_transformers.openai_transformer import OpenAIPromptTransformer
from app.config import Settings


def test_transformer_cleanup_rules():
    settings = Settings(openai_api_key=None)
    transformer = OpenAIPromptTransformer(settings)
    raw = """
0:01 쇼츠 오프닝\nShot 1: 카메라 줌인\n#핫플레이스\nCTA: 구독과 좋아요\n자막: 오늘의 메뉴 소개\nInstagram용 쇼츠\n"""
    output = transformer._sanitize_brief(raw)
    lowered = output.lower()
    assert "#" not in output
    assert "shot" not in lowered
    assert "cta" not in lowered
    assert "자막" not in lowered
    assert "instagram" not in lowered
