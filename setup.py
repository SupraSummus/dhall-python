from setuptools import setup
from distutils.command.build import build
import subprocess
import sys


def compile_parser():
    # patch grammar
    subprocess.run(
        ['patch', '--binary', '-o', 'dhall.abnf', 'dhall-lang/standard/dhall.abnf', 'dhall.abnf.patch'],
        check=True,
    )

    # convert into bnf
    from abnf2bnf import abnf2bnf
    with open('dhall.abnf', 'rb') as f:
        # reading binary, to preserve /r/n line endings
        abnf_grammar = f.read().decode('utf8')
    grammar = abnf2bnf(abnf_grammar, 'complete-expression')

    # calculate parse tables
    from bnf2parglare import bnf2parglare, make_external_recognizers
    grammar = make_external_recognizers(*grammar, [
        'simple-label',
        'single-quote-regular-chunk',
    ])
    compiled_grammar = bnf2parglare(*grammar)

    # save into python
    with open('dhall/_grammar.py', 'wt') as f:
        f.write('grammar = ')
        f.write(repr(compiled_grammar))
        f.write('\n')


class custom_build(build):
    def run(self):
        if not self.dry_run:
            compile_parser()
        build.run(self)


requirements = [
    'parglare',
    'pyrsistent==0.14.*',
    'attrs',
]

setup(
    name='dhall-python',
    version='0.0.0',
    description='Pure python implementation of dhall lang',
    license='MIT',
    url='https://github.com/SupraSummus/dhall-python',
    keywords='dhall',
    py_modules=['dhall'],
    scripts=[
        'bin/dhall-python-parse',
    ],
    setup_requires=[
        'parglare',
        'click',  # parglare dependency
    ],
    install_requires=requirements,
    tests_require=[
        'parameterized',
    ] + requirements,
    dependency_links=[
        'https://github.com/SupraSummus/parglare/archive/4d8023eb42e2466474c46b425f2c7fd64fb22e38.zip#egg=parglare'
    ],
    cmdclass={
        'build': custom_build,
    },
)
