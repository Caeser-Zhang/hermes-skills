require 'spec_helper'
require_relative '../app/services/email_service'

RSpec.describe 'EmailService' do
  let(:email_service) { EmailService.new }
  let(:user) { double('User', email: 'test@example.com', name: 'Test User') }
  let(:mailer) { double('Mailer') }
  
  before(:each) do
    allow(EmailService).to receive(:mailer).and_return(mailer)
  end
  
  describe '#send_welcome_email' do
    context 'with valid user' do
      before do
        allow(mailer).to receive(:send).and_return(true)
      end
      
      it 'sends welcome email' do
        email_service.send_welcome_email(user)
        expect(mailer).to have_received(:send).with(
          to: user.email,
          subject: 'Welcome!',
          body: instance_of(String)
        )
      end
      
      it 'returns true' do
        result = email_service.send_welcome_email(user)
        expect(result).to be_truthy
      end
    end
    
    context 'with invalid user' do
      let(:invalid_user) { double('User', email: nil, name: 'Invalid') }
      
      it 'raises ArgumentError' do
        expect { email_service.send_welcome_email(invalid_user) }.to raise_error(ArgumentError)
      end
    end
    
    context 'when mailer fails' do
      before do
        allow(mailer).to receive(:send).and_raise(NetworkError)
      end
      
      it 'raises EmailServiceError' do
        expect { email_service.send_welcome_email(user) }.to raise_error(EmailServiceError)
      end
      
      it 'logs the error' do
        expect(email_service.logger).to receive(:error).with(/NetworkError/)
        email_service.send_welcome_email(user) rescue EmailServiceError
      end
    end
  end
  
  describe '#send_notification' do
    it 'sends notification with correct parameters' do
      allow(mailer).to receive(:send).and_return(true)
      
      email_service.send_notification(
        user,
        title: 'Update Available',
        message: 'New version is ready'
      )
      
      expect(mailer).to have_received(:send).with(
        to: user.email,
        subject: 'Update Available',
        body: include('New version is ready')
      )
    end
  end
  
  describe '#bulk_send' do
    let(:users) { [user, double('User', email: 'user2@example.com')] }
    
    it 'sends email to all users' do
      allow(mailer).to receive(:send).and_return(true)
      
      results = email_service.bulk_send(users, subject: 'Bulk Test', body: 'Test')
      
      expect(results).to all(be_truthy)
    end
    
    it 'continues on individual failures' do
      allow(mailer).to receive(:send).and_raise(NetworkError).and_return(true)
      
      results = email_service.bulk_send(users, subject: 'Test', body: 'Test')
      
      expect(results.count(true)).to eq(1)
    end
  end
end
