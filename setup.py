from distutils.core import setup
setup(
  name = 'recipe_to_rensa',
  packages = ['recipe_to_rensa'],
  package_data={'recipe_to_rensa': ['assertions/*','input/*']},
  version = '0.0.1',
  description = 'Extract and realize culinary recipes.',
  author = 'Sarah Harmon',
  author_email = 'sharmon@bowdoin.edu',
  url = 'https://github.com/RensaProject/recipe_to_rensa',
  classifiers = [],
)
