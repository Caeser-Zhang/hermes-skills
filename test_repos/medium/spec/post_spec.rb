require 'spec_helper'
require_relative '../app/models/user'
require_relative '../app/models/post'

RSpec.describe 'Post' do
  let(:author) { User.new(id: 1, name: 'Alice', email: 'alice@example.com') }
  let!(:post) { Post.new(title: 'Test Post', content: 'Content here', author: author) }
  
  before(:each) do
    # Setup for each test
    @comment_count = 0
  end
  
  after(:each) do
    # Cleanup after each test
    post.comments.clear
  end
  
  describe '#valid?' do
    context 'with all required fields' do
      it 'returns true' do
        expect(post.valid?).to be_truthy
      end
    end
    
    context 'without title' do
      before { post.title = nil }
      
      it 'returns false' do
        expect(post.valid?).to be_falsy
      end
      
      it 'includes title in errors' do
        post.valid?
        expect(post.errors).to include(:title)
      end
    end
    
    context 'without content' do
      before { post.content = nil }
      
      it 'returns false' do
        expect(post.valid?).to be_falsy
      end
    end
  end
  
  describe '#publish!' do
    it 'sets published_at timestamp' do
      expect { post.publish! }.to change { post.published_at }.from(nil)
    end
    
    it 'sets status to published' do
      post.publish!
      expect(post.status).to eq('published')
    end
    
    it 'raises error if already published' do
      post.publish!
      expect { post.publish! }.to raise_error(AlreadyPublishedError)
    end
  end
  
  describe '#add_comment' do
    it 'adds comment to post' do
      comment = Comment.new(body: 'Great post!')
      post.add_comment(comment)
      expect(post.comments).to include(comment)
    end
    
    it 'increments comment count' do
      comment = Comment.new(body: 'Nice!')
      expect { post.add_comment(comment) }.to change { post.comments.count }.by(1)
    end
  end
  
  describe '#word_count' do
    it 'counts words in content' do
      expect(post.word_count).to eq(2)  # "Content here"
    end
    
    it 'returns 0 for empty content' do
      post.content = ''
      expect(post.word_count).to eq(0)
    end
    
    it 'returns 0 for nil content' do
      post.content = nil
      expect(post.word_count).to eq(0)
    end
  end
  
  describe '#author_name' do
    it 'returns author name' do
      expect(post.author_name).to eq('Alice')
    end
    
    it 'returns "Unknown" if no author' do
      post.author = nil
      expect(post.author_name).to eq('Unknown')
    end
  end
end
