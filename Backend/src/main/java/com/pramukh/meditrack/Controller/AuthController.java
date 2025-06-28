package com.pramukh.meditrack.Controller;

import com.pramukh.meditrack.Component.JWTUtil;
import com.pramukh.meditrack.DTO.LoginDto;
import com.pramukh.meditrack.DTO.SignUpDTO;
import com.pramukh.meditrack.Models.User;
import com.pramukh.meditrack.Repository.UserRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class AuthController {
    private AuthenticationManager authManager;
    private UserRepository userRepo;
    private JWTUtil jwtUtil;

    @Autowired
    public AuthController(AuthenticationManager authManager, UserRepository userRepo, JWTUtil jwtUtil) {
        this.authManager = authManager;
        this.userRepo = userRepo;
        this.jwtUtil = jwtUtil;
    }

    @PostMapping("/signup")
    public ResponseEntity<String> signup(@RequestBody SignUpDTO req) {
        if (userRepo.findByEmail(req.email).isPresent()) {
            return ResponseEntity.badRequest().body("Email already exists");
        }

        User user = new User();
        user.setFirstName(req.firstName);
        user.setLastName(req.lastName);
        user.setEmail(req.email);
        user.setPassword(new BCryptPasswordEncoder().encode(req.password));
        user.setRole(req.role);
        user.setGender(req.gender);
        user.setDateOfBirth(req.dateOfBirth);
        user.setPhoneNumber(req.phoneNumber);
        user.setInsuranceNumber(req.insuranceNumber);
        user.setAddress(req.address);

        userRepo.save(user);
        return ResponseEntity.ok("User registered successfully");
    }

    @PostMapping("/login")
    public ResponseEntity<String> login(@RequestBody LoginDto req) {
        authManager.authenticate(new UsernamePasswordAuthenticationToken(req.email, req.password));
        User user = userRepo.findByEmail(req.email).orElseThrow(() -> new UsernameNotFoundException("User not found"));
        String token = jwtUtil.generateToken(user.getEmail(), user.getRole());
        return ResponseEntity.ok(token);
    }
}
