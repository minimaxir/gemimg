from setuptools import setup

setup(
    name="gemimg",
    packages=["gemimg"],
    version="0.1.0",
    description="Lightweight wrapper for generating and editing images from Gemini 2.5 Flash Image.",
    long_description=open("README.md", "r", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Max Woolf",
    author_email="max@minimaxir.com",
    url="https://github.com/minimaxir/gemimg",
    keywords=["chatgpt", "openai", "text generation", "ai"],
    classifiers=[],
    license="MIT",
    python_requires=">=3.10",
    install_requires=[
        "httpx>=0.28.1",
        "python-dotenv>=1.1.1",
        "orjson>=3.11.3",
    ],
)
