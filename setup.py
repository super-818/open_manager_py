from setuptools import setup, find_packages

setup(
    name='open_manager_py',
    version='0.3.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Flask>=2.0.0',
        'PyYAML>=5.4',
        'click>=8.0.0',
    ],
    entry_points={
        'console_scripts': [
            'open-manager=open_manager_py.app:main',
            'open-manager-cli=open_manager_py.cli:main',
        ],
    },
    author='Open Manager',
    description='开源技能与GitHub项目管理器 - Web+CLI',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.8',
)
