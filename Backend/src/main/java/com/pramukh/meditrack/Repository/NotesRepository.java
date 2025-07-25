package com.pramukh.meditrack.Repository;

import com.pramukh.meditrack.Models.NotesModels.Notes;
import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface NotesRepository extends MongoRepository<Notes, String> {


    Optional<Object> findByInsuranceNumber(String insuranceNumber);
}
