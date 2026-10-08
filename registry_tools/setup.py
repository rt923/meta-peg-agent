"""setup.py — registry_tools pip 包配置"""

from setuptools import setup, find_packages

setup(
    name="registry_tools",
    version="0.1.0",
    description="PEP-A 登记册一致性工具集：fix_versions_refs + auto_register_versions",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="PEG-A Team",
    url="https://github.com/your-org/registry_tools",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=[],
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
            "registry-check = registry_tools.fix_versions_refs:main",
            "registry-fix = registry_tools.fix_versions_refs:main",
            "registry-register = registry_tools.auto_register_versions:main",
        ],
    },
)