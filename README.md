# CF - automatic tester for programming Codeforces contests

## Features

- extract sample test cases (inputs and outputs)
- ability to add and remove custom tests

## Create new contest

```
usage: cf.py contest id [-t TYPE] [-l LANG]

positional arguments:
  id                    Contest id

optional arguments:
  -t TYPE, --type TYPE  Type of contest (e.g. contest, gym...)
  -l LANG, --lang LANG  Language you want to use
```

## Testing

```
usage: cf.py test problem [-a] [-r]

positional arguments:
  problem       Problem letter

optional arguments:
  -a, --add     Add your test
  -r, --remove  Remove last test
```

## Changelog

### Version 0.1 (2019.04.30)

- Initial release
