from setuptools import setup, find_namespace_packages
from pathlib import Path

long_description = (Path(__file__).parent / "README.md").read_text(encoding="utf-8") if (Path(__file__).parent / "README.md").exists() else ""

setup(
    name='open-manager-py',
    version='0.7.0',
    description='开源技能与GitHub项目管理器 - Web UI + CLI，统一管理AI skills和GitHub仓库',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='super-818',
    author_email='1****************@******',
    url='https://github.com/super-818/open_manager_py',
    packages=find_namespace_packages(exclude=['tests', 'tests.*']),
    include_package_data=True,
    package_data={
        'open_manager_py': [
            'templates/*.html',
            'static/css/*.css',
            'static/js/*.js',
        ],
    },
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
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Topic :: Software Development :: Version Control :: Git',
        'Topic :: System :: Software Distribution',
    ],
    keywords='github skills manager ai agent project-management',
    python_requires='>=3.8',
    license='MIT',
)
