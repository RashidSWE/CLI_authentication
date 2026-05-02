from setuptools import setup, find_packages

setup(
    name="insighta",
    version="0.1.0",
    packages=find_packages(),
    py_modules=["main", "auth", "config"],
    install_requires=[
        "requests",
        "typer"
    ],
    entry_points={
        "console_scripts":[
            "insighta=main:cli"
        ]
    }
)