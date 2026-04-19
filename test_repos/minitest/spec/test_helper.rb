require 'minitest/autorun'

# Test configuration
class Minitest::Test
  def setup
    # Global setup
  end
  
  def teardown
    # Global teardown
  end
end

# Test helpers
module TestHelpers
  def create_test_user(overrides = {})
    User.create({
      name: 'Test User',
      email: 'test@example.com'
    }.merge(overrides))
  end
  
  def assert_validates_presence(model, attribute)
    model.send("#{attribute}=", nil)
    refute model.valid?
    assert_includes model.errors[attribute], "can't be blank"
  end
end

# Include helpers in all tests
Minitest::Test.include(TestHelpers)
