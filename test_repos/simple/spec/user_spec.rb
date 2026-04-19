require 'spec_helper'

RSpec.describe 'User' do
  let(:user) { User.new(name: 'John Doe', email: 'john@example.com') }
  
  describe '#valid?' do
    it 'returns true for valid user' do
      expect(user.valid?).to be_truthy
    end
    
    it 'returns false for user without email' do
      user.email = nil
      expect(user.valid?).to be_falsy
    end
  end
  
  describe '#admin?' do
    it 'returns false for regular user' do
      expect(user.admin?).to be_falsy
    end
    
    it 'returns true for admin user' do
      user.role = 'admin'
      expect(user.admin?).to be_truthy
    end
  end
  
  describe '#to_s' do
    it 'returns formatted string' do
      expect(user.to_s).to eq('John Doe (john@example.com)')
    end
  end
end
