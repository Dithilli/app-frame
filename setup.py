from setuptools import setup, find_packages

VERSION = '0.10.0'
REQUIREMENTS = [
    'Flask-DotEnv==0.1.1',
    'Flask-Login==0.4.1',
    'Flask-WTF==0.14.2',
    'Flask==1.0.2',
    'Jinja2==2.10',
    'MarkupSafe==1.0',
    'Werkzeug==0.14.1',
    'arrow==0.12.1',
    'click==6.7',
    'fastavro==0.21.4',
    'gevent==1.3.5',
    'greenlet==0.4.14',
    'itsdangerous==0.24',
    'python-oauth2==1.1.0',
    'requests==2.19.1',
    'ulid-py==0.0.6',
    'hvac==0.6.3',
]
SETUP_REQUIREMENTS = []
TEST_REQUIREMENTS = []

setup(
    name='ecselfservice',
    author='data engineering',
    author_email='de@wework.com',
    classifiers=[
        'Development Status :: 4 - Beta'
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3.6',
    ],
    description='github oauth demo',
    long_description='github oauth demo',
    include_package_data=True,
    packages=find_packages(),
    install_requires=REQUIREMENTS,
    setup_requires=SETUP_REQUIREMENTS,
    tests_require=TEST_REQUIREMENTS,
    test_suite='tests',
    version=VERSION,
    zip_safe=False,
)
