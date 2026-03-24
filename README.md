# 202411016

github repo link: 

## How To Run Code

### Integration (Street Race Manager)

```bash
cd integration/code
python3 main.py
```

### Whitebox (MoneyPoly)

```bash
cd whitebox/code/moneypoly
python3 main.py
```

## How To Run Tests

### Integration tests

```bash
cd integration
python3 -m pytest tests -q
```

### Whitebox tests

```bash
cd whitebox/tests
python3 -m pytest whitebox_tests.py -q
```

### Blackbox API tests

```bash
cd blackbox
python3 -m pytest tests -q
```
