require 'spec_helper'

RSpec.describe 'Calculator' do
  describe '#add' do
    it 'returns the sum of two numbers' do
      calculator = Calculator.new
      result = calculator.add(2, 3)
      expect(result).to eq(5)
    end
    
    it 'handles negative numbers' do
      calculator = Calculator.new
      result = calculator.add(-1, -2)
      expect(result).to eq(-3)
    end
  end
  
  describe '#subtract' do
    it 'returns the difference of two numbers' do
      calculator = Calculator.new
      result = calculator.subtract(5, 3)
      expect(result).to eq(2)
    end
  end
end
