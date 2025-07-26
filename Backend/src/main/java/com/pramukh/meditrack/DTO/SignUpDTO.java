package com.pramukh.meditrack.DTO;

import com.pramukh.meditrack.Models.ENUM.Role;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class SignUpDTO {
    private String firstName;
    private String lastName;
    private String email;
    private String password;
    private Role role;
}
