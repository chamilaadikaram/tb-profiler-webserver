from setuptools import find_packages, setup

setup(
    name='tb-profiler-webserver',
    version='0.1.5',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'flask',
    ],
)
