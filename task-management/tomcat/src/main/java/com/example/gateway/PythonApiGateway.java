package com.example.gateway;

import jakarta.servlet.ServletException;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.HttpServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;

@WebServlet(urlPatterns = "/api/*")
public class PythonApiGateway extends HttpServlet {
    private HttpClient client;
    private String pythonApiUrl;

    @Override
    public void init() throws ServletException {
        client = HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(5))
                .build();
        pythonApiUrl = System.getenv().getOrDefault("PYTHON_API_URL", "http://python-api:5000");
    }

    @Override protected void doGet(HttpServletRequest req, HttpServletResponse res) throws IOException {
        forward(req, res, "GET");
    }

    @Override protected void doPost(HttpServletRequest req, HttpServletResponse res) throws IOException {
        forward(req, res, "POST");
    }

    @Override protected void doPut(HttpServletRequest req, HttpServletResponse res) throws IOException {
        forward(req, res, "PUT");
    }

    @Override protected void doDelete(HttpServletRequest req, HttpServletResponse res) throws IOException {
        forward(req, res, "DELETE");
    }

    private void forward(HttpServletRequest req, HttpServletResponse res, String method) throws IOException {
        String path = req.getPathInfo() == null ? "/" : req.getPathInfo();
        String query = req.getQueryString();
        String target = pythonApiUrl + path + (query == null ? "" : "?" + query);

        HttpRequest.BodyPublisher body = ("POST".equals(method) || "PUT".equals(method))
                ? HttpRequest.BodyPublishers.ofByteArray(req.getInputStream().readAllBytes())
                : HttpRequest.BodyPublishers.noBody();

        HttpRequest request = HttpRequest.newBuilder(URI.create(target))
                .timeout(Duration.ofSeconds(30))
                .header("Content-Type", req.getContentType() == null ? "application/json" : req.getContentType())
                .method(method, body)
                .build();

        try {
            HttpResponse<byte[]> response = client.send(request, HttpResponse.BodyHandlers.ofByteArray());
            res.setStatus(response.statusCode());
            String contentType = response.headers().firstValue("Content-Type").orElse("application/json; charset=utf-8");
            res.setContentType(contentType);
            if (response.body().length > 0) {
                res.getOutputStream().write(response.body());
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            res.sendError(HttpServletResponse.SC_BAD_GATEWAY, "Python API request interrupted");
        } catch (Exception e) {
            getServletContext().log("Python API forwarding failed", e);
            res.sendError(HttpServletResponse.SC_BAD_GATEWAY, "Python API unavailable");
        }
    }
}
