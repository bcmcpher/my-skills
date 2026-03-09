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

Place `// AI-Generated` above each `TEST` or `TEST_F` block:

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

## Test structure patterns

### Arrange / Act / Assert

```cpp
// AI-Generated
TEST(DivideTest, ReturnsCorrectQuotient) {
    // Arrange
    int numerator = 10;
    int denominator = 2;

    // Act
    int result = divide(numerator, denominator);

    // Assert
    EXPECT_EQ(result, 5);
}

// AI-Generated
TEST(DivideTest, ThrowsOnZeroDivisor) {
    EXPECT_THROW(divide(1, 0), std::domain_error);
}
```

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

## Dependency isolation (mocking — Google Mock)

Google Mock (gmock) ships with Google Test. Unit tests must not call real filesystems,
networks, or databases. Use mock objects by defining an abstract interface and a mock
implementation.

### Check availability

```cmake
# CMakeLists.txt should include:
target_link_libraries(tests gmock_main)
```

### Define an interface (pure virtual class)

```cpp
// database.h
class IDatabase {
public:
    virtual ~IDatabase() = default;
    virtual bool save(int id, const std::string& value) = 0;
    virtual std::string load(int id) = 0;
};
```

### Create a mock class

```cpp
// mock_database.h
#include <gmock/gmock.h>
#include "database.h"

class MockDatabase : public IDatabase {
public:
    MOCK_METHOD(bool, save, (int id, const std::string& value), (override));
    MOCK_METHOD(std::string, load, (int id), (override));
};
```

### Use the mock in tests

```cpp
#include "mock_database.h"
#include "record_service.h"

// AI-Generated
TEST(RecordServiceTest, SaveCallsDatabaseSave) {
    // Arrange
    MockDatabase mock_db;
    RecordService service(&mock_db);
    EXPECT_CALL(mock_db, save(1, "hello")).WillOnce(::testing::Return(true));

    // Act
    bool result = service.saveRecord(1, "hello");

    // Assert
    EXPECT_TRUE(result);
}

// AI-Generated
TEST(RecordServiceTest, LoadReturnsValueFromDatabase) {
    // Arrange
    MockDatabase mock_db;
    RecordService service(&mock_db);
    ON_CALL(mock_db, load(1)).WillByDefault(::testing::Return("hello"));

    // Act
    std::string result = service.loadRecord(1);

    // Assert
    EXPECT_EQ(result, "hello");
}
```

### Common Google Mock matchers

```cpp
EXPECT_CALL(mock, method(::testing::_));           // any argument
EXPECT_CALL(mock, method(::testing::Eq(42)));      // equal to 42
EXPECT_CALL(mock, method(::testing::Gt(0)));       // greater than 0
EXPECT_CALL(mock, method(::testing::HasSubstr("x"))); // string contains
EXPECT_CALL(mock, method(...)).Times(1);           // called exactly once
EXPECT_CALL(mock, method(...)).Times(::testing::AtLeast(1));
```

## Catch2 (alternative)

```cpp
#include <catch2/catch_test_macros.hpp>

// AI-Generated
TEST_CASE("add returns correct sum", "[math]") {
    // Arrange / Act / Assert
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
