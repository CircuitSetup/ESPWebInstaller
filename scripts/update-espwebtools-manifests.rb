require 'uri'
require 'json'

manifest = {
  name: ENV['MANIFEST_NAME'],
  version: ENV['MANIFEST_VERSION'],
  builds: []
}

if ENV['ESP32_IMAGE_URI']
  manifest[:builds] << {
    chipFamily: 'ESP32',
    parts: [
      { path: ENV['ESP32_IMAGE_URI'], offset: 0 }
    ]
  }
end

if ENV['ESP32_S3_IMAGE_URI']
  manifest[:builds] << {
    chipFamily: 'ESP32-S3',
    parts: [
      { path: ENV['ESP32_S3_IMAGE_URI'], offset: 0 }
    ]
  }
end
json = JSON.dump(manifest)
puts json
File.write("manifests/#{ENV['MANIFEST_FNAME']}", json)
