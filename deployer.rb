#!/usr/bin/env ruby

require 'json'
require 'net/http'
require 'openssl'
require 'uri'

def orlo_request(method, url, body = nil)
    if $http.nil?
        return
    end

    puts " -> %s" % [ url ]

    request  = method.new(url, initheader = {
        "Content-Type" => "application/json"
    })
    request.basic_auth("testuser", "blabla")

    if ! body.nil?
        request.body = JSON(body)
    end

    response = $http.request(request)

    if ! response.kind_of?(Net::HTTPSuccess)
        raise "#{request.path} returned #{response.code}"
    end

    if ! response.body.nil? and response.body.length > 0
        JSON.parse(response.body)
    end
end

def orlo_get(url)
    orlo_request(Net::HTTP::Get, url)
end

def orlo_post(url, body = nil)
    orlo_request(Net::HTTP::Post, url, body)
end

puts "Dummy Deployer v0.1"

if ENV["ORLO_URL"].nil?
    $http = nil
else
    $uri  = URI.parse(ENV["ORLO_URL"])
    $http = Net::HTTP.new($uri.host, $uri.port)
    if $uri.is_a?(URI::HTTPS)
        $http.use_ssl = true
#       $http.verify_mode = OpenSSL::SSL::VERIFY_NONE
    end
end

if ENV["ORLO_RELEASE"]
    releases = orlo_get("/releases/#{ENV["ORLO_RELEASE"]}")
    release  = releases["releases"][0]
    deployables = release["packages"].collect do |package|
        [ package["name"], package["version"] ]
    end
else
    release = orlo_post("/releases", {
        "user"       => ENV["ORLO_USER"],
        "team"       => ENV["ORLO_TEAM"],
        "platforms"  => ENV["ORLO_PLATFORMS"],
        "references" => ENV["ORLO_REFERENCES"],
    })
    deployables = ARGV.collect do |deployable|
        deployable.split("=")
    end
end

if release
    puts "Orlo release ID #{release["id"]}"
end

deployables.each do |deployable|
    pkgname, version = deployable

    if release
        package = orlo_post("/releases/#{release["id"]}/packages", {
            "name"     => pkgname,
            "version"  => version,
            "rollback" => !ENV["ORLO_ROLLBACK"].nil?,
        })
    end

    puts "Installing #{pkgname} version #{version}"

    if release
        orlo_post("/releases/#{release["id"]}/packages/#{package["id"]}/start")
    end

    puts "# apt-get install #{pkgname}=#{version}"
    sleep 1 # ... wow, much install ...

    if release
        orlo_post("/releases/#{release["id"]}/packages/#{package["id"]}/stop", {
            "success" => true,
        })
    end
end

if release
    orlo_post("/releases/#{release["id"]}/stop")
end

puts "Finished!"
exit 0
