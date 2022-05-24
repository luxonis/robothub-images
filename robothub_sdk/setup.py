import io

from setuptools import setup

with open('requirements.txt') as f:
    required = f.readlines()

setup(
    name='robothub-sdk',
    version='0.0.2',
    description='RobotHub SDK is a Python package allowing you to write Perception Apps',
    long_description=io.open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url='https://www.luxonis.com/',
    keywords="robothub sdk depthai robot hub connect agent",
    author='Luxonis',
    author_email='support@luxonis.com',
    packages=['robothub_sdk'],
    package_dir={"": "src"},  # https://stackoverflow.com/a/67238346/5494277
    install_requires=required,
    include_package_data=True,
    project_urls={
        "Documentation": "https://docs.luxonis.com/projects/robothub/en/latest/",
    },
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
)
