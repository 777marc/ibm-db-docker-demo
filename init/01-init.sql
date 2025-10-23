-- Create a sample table and insert test data
CREATE TABLE USERS (
    ID INTEGER NOT NULL GENERATED ALWAYS AS IDENTITY,
    NAME VARCHAR(100) NOT NULL,
    EMAIL VARCHAR(255) NOT NULL,
    CREATED_AT TIMESTAMP DEFAULT CURRENT TIMESTAMP,
    PRIMARY KEY (ID)
);

-- Insert some test data
INSERT INTO USERS (NAME, EMAIL) VALUES
    ('John Doe', 'john@example.com'),
    ('Jane Smith', 'jane@example.com'),
    ('Bob Wilson', 'bob@example.com');

-- Grant permissions to db2inst1
GRANT ALL ON TABLE USERS TO USER db2inst1;