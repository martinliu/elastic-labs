# `gem install elastic-app-search progress_bar`

require 'elastic-app-search'
require 'json'
require 'progress_bar'

API_ENDPOINT = 'http://192.168.50.10:3002/api/as//v1/'
API_KEY = 'private-a5nxebqyrggp2wm8q7xdfgbu'
ENGINE_NAME = 'games'

client = Elastic::AppSearch::Client.new(:api_key => API_KEY, :api_endpoint => API_ENDPOINT)
file = File.read('./video-games.json')
data = JSON.parse(file)
bar = ProgressBar.new(data.count / 100)

data.each_slice(100) do |slice|
  client.index_documents(ENGINE_NAME, slice)
  bar.increment!
end
