require 'test_helper'
require_relative '../app/services/user_service'

class UserServiceTest < Minitest::Test
  def setup
    @service = UserService.new
    @user_data = { name: 'John Doe', email: 'john@example.com' }
  end
  
  def teardown
    # Cleanup after tests
    User.delete_all
  end
  
  def test_create_user_with_valid_data
    user = @service.create(@user_data)
    
    assert user.persisted?
    assert_equal 'John Doe', user.name
    assert_equal 'john@example.com', user.email
  end
  
  def test_create_user_requires_name
    @user_data.delete(:name)
    
    assert_raises(ValidationError) do
      @service.create(@user_data)
    end
  end
  
  def test_create_user_requires_email
    @user_data.delete(:email)
    
    assert_raises(ValidationError) do
      @service.create(@user_data)
    end
  end
  
  def test_find_user_by_id
    created = @service.create(@user_data)
    found = @service.find(created.id)
    
    assert_equal created, found
  end
  
  def test_find_user_returns_nil_for_invalid_id
    result = @service.find(999999)
    
    assert_nil result
  end
  
  def test_update_user
    user = @service.create(@user_data)
    updated = @service.update(user.id, name: 'Jane Doe')
    
    assert_equal 'Jane Doe', updated.name
    assert_equal user.email, updated.email
  end
  
  def test_delete_user
    user = @service.create(@user_data)
    
    assert @service.delete(user.id)
    assert_nil @service.find(user.id)
  end
  
  def test_list_users
    @service.create(@user_data)
    @service.create(name: 'Jane', email: 'jane@example.com')
    
    users = @service.list
    
    assert_equal 2, users.length
  end
  
  def test_list_users_with_pagination
    5.times { |i| @service.create(name: "User#{i}", email: "user#{i}@example.com") }
    
    page1 = @service.list(page: 1, per_page: 2)
    page2 = @service.list(page: 2, per_page: 2)
    
    assert_equal 2, page1.length
    assert_equal 2, page2.length
  end
end
