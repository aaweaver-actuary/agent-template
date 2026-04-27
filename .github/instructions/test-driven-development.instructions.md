---
description: Whenever you are writing code, you should follow the principles of test-driven development (TDD). 
applyTo: '**/*.*'
---

# Test-Driven Development (TDD) Instructions

## Applies to:
- All programming languages and file types.

## Principles of TDD:
1. **Write a Test**: Before writing any functional code, write a test that defines a function or improvements of a function.
2. **Make Sure the Test Fails**: Run the test to ensure that it fails. This step confirms that the test is valid and that the functionality being tested does not yet exist.
3. **Write the Minimum Code to Pass the Test**: Write just enough code to make the test pass. Focus on simplicity and avoid writing any extra code that is not necessary for passing the test.
4. **Write _ONLY_ Enough Code to Pass the Test**: Do not write any additional code that is not required to pass the test. This helps to keep the codebase clean and maintainable.
5. **Refactor**: After the test passes, refactor the code to improve its structure and readability without changing its behavior. This step helps to ensure that the code is clean and efficient.
6. **Repeat**: Repeat the cycle for each new piece of functionality or improvement.

## Red-Green-Refactor Cycle:
- **Red**: Write a test and see it fail.
- **Green**: Write the minimum code to make the test pass.
- **Refactor**: Clean up the code while ensuring that all tests still pass.