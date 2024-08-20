from setuptools import setup, find_packages

setup(
    name="eventbridge-client",
    version="0.4.11",
    packages=find_packages(),
    install_requires=[
        "boto3",
        "jsonschema",
        "requests",
    ],
    author="Apurv Hajare",
    author_email="apurv@karboncard.com",
    description="A simple EventBridge client for producing and consuming events with Schema Validation.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://bitbucket.org/credit-application/eventbridge-client",
)
