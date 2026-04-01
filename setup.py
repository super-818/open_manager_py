from setuptools import setup, find_packages

setup(
    name='open_manager_py',
    version='0.1.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Flask>=2.0.0',
    ],
    entry_points={
        'console_scripts': [
            'open-manager=open_manager_py.app:main',
        ],
    },
    author='Open Manager',
    description='开源资源管理器 - Web版本',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.7',
)