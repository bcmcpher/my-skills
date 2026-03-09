# C/C++ Testing Reference

## Frameworks

Check the build system (`CMakeLists.txt`, `Makefile`) for the configured framework:

- **Google Test (gtest)** — most common for C++; also handles C with some adaptation
- **Catch2** — header-only, common in smaller projects
- **Unity** — lightweight, common for embedded C

This reference covers Google Test primarily, with Catch2 notes.

## Test file location

- `tests/test_<module>.cpp` or `<module>_test.cpp`
- Register with CMake: `add_executable(tests ...) target_link_libraries(tests gtest_main)`

## Running tests (Google Test)

```bash
# Build first (CMake example)
cmake -B build && cmake --build build

# Run all tests
./build/tests

# Run specific test
./build/tests --gtest_filter=MyClass.MethodName

# Verbose
./build/tests --gtest_verbose
```

## AI-generated marker

C/C++ has no decorator system. Place `// AI-Generated` above each `TEST` or `TEST_F` block:

```cpp
// AI-Generated
TEST(AddTest, PositiveNumbers) {
    EXPECT_EQ(add(2, 3), 5);
}

// AI-Generated
TEST(AddTest, ThrowsOnNullPointer) {
    EXPECT_THROW(process(nullptr), std::invalid_argument);
}
```

## Google Test patterns

### Basic assertions

```cpp
EXPECT_EQ(result, expected);       // equality
EXPECT_NE(result, unexpected);     // inequality
EXPECT_LT(a, b);                   // a < b
EXPECT_GT(a, b);                   // a > b
EXPECT_NEAR(a, b, tolerance);      // float comparison
EXPECT_TRUE(condition);
EXPECT_FALSE(condition);
EXPECT_THROW(expr, ExceptionType); // throws specific exception
EXPECT_NO_THROW(expr);             // does not throw
```

### Test fixtures (shared setup)

```cpp
class MyClassTest : public ::testing::Test {
protected:
    void SetUp() override {
        obj = new MyClass(42);
    }
    void TearDown() override {
        delete obj;
    }
    MyClass* obj;
};

// AI-Generated
TEST_F(MyClassTest, GetValueReturnsConstructorArg) {
    EXPECT_EQ(obj->getValue(), 42);
}

// AI-Generated
TEST_F(MyClassTest, SetValueUpdatesState) {
    obj->setValue(99);
    EXPECT_EQ(obj->getValue(), 99);
}
```

### Parametrized tests

```cpp
class AddParamTest : public ::testing::TestWithParam<std::tuple<int, int, int>> {};

// AI-Generated
TEST_P(AddParamTest, ReturnsCorrectSum) {
    auto [a, b, expected] = GetParam();
    EXPECT_EQ(add(a, b), expected);
}

INSTANTIATE_TEST_SUITE_P(
    AddCases, AddParamTest,
    ::testing::Values(
        std::make_tuple(1, 2, 3),
        std::make_tuple(0, 0, 0),
        std::make_tuple(-1, 1, 0)
    )
);
```

## Catch2 (alternative)

```cpp
#include <catch2/catch_test_macros.hpp>

// AI-Generated
TEST_CASE("add returns correct sum", "[math]") {
    REQUIRE(add(2, 3) == 5);
    REQUIRE(add(-1, 1) == 0);
}

// AI-Generated
TEST_CASE("divide throws on zero divisor", "[math]") {
    REQUIRE_THROWS_AS(divide(1, 0), std::domain_error);
}
```

## Expected failures (source bugs)

```cpp
// AI-Generated — DISABLED: Bug in edge case, see issue #15
TEST(DISABLED_MyTest, FloatPrecisionEdgeCase) {
    EXPECT_NEAR(divide(1.0f, 3.0f) * 3.0f, 1.0f, 1e-6f);
}
```
