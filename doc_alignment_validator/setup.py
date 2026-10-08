"""setup.py — doc_alignment_validator pip 包配置"""

from setuptools import setup, find_packages

setup(
    name="doc_alignment_validator",
    version="0.1.0",
    description="doc_alignment JSON 完整性校验工具（11 项检查）",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="PEG-A Team",
    url="https://github.com/your-org/doc_alignment_validator",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    package_data={
        "doc_alignment_validator": [
            "data/doc_alignment.json",
        ],
    },
    include_package_data=True,
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.12",
    ],
    entry_points={
        "console_scripts": [
            "doc-alignment-validate = doc_alignment_validator.validate:main",
        ],
    },
)