from setuptools import setup, find_packages

setup(
    name='django-slack-sync',
    version='1.0.0',
    packages=find_packages(),
    url='https://github.com/alexsilva/django-slack-sync',
    license='MIT',
    author='alex',
    author_email='alex@fabricadigital.com.br',
    description='Synchronizing slack users and sending targeted messages.',
    install_requires=['slackbot']
)
