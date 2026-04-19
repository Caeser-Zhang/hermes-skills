require 'test_helper'
require_relative '../app/models/calculator'

class CalculatorTest < Minitest::Test
  def setup
    @calculator = Calculator.new
  end
  
  def test_add_returns_sum
    result = @calculator.add(2, 3)
    assert_equal 5, result
  end
  
  def test_add_handles_negative_numbers
    result = @calculator.add(-1, -2)
    assert_equal(-3, result)
  end
  
  def test_subtract_returns_difference
    result = @calculator.subtract(5, 3)
    assert_equal 2, result
  end
  
  def test_multiply_returns_product
    result = @calculator.multiply(4, 3)
    assert_equal 12, result
  end
  
  def test_divide_returns_quotient
    result = @calculator.divide(10, 2)
    assert_equal 5, result
  end
  
  def test_divide_raises_error_for_zero
    assert_raises(DivisionByZeroError) do
      @calculator.divide(10, 0)
    end
  end
  
  def test_power_returns_exponent
    result = @calculator.power(2, 3)
    assert_equal 8, result
  end
  
  def test_sqrt_returns_square_root
    result = @calculator.sqrt(16)
    assert_in_delta 4.0, result, 0.001
  end
  
  def test_sqrt_raises_error_for_negative
    assert_raises(ArgumentError) do
      @calculator.sqrt(-1)
    end
  end
end
